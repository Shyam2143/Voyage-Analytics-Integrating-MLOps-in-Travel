pipeline {
    agent any

    environment {
        IMAGE_NAME = 'dmcshyam/flight-price-predictor'
        IMAGE_TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('Get code') {
            steps {
                checkout scm
            }
        }

        stage('Build image') {
            steps {
                dir('Flight price prediction') {
                    sh 'docker build -t $IMAGE_NAME:$IMAGE_TAG .'
                }
            }
        }

        stage('Test image') {
            steps {
                sh '''
                    docker run -d --name flight-price-test -p 18000:8000 "$IMAGE_NAME:$IMAGE_TAG"

                    attempt=0
                    until docker exec flight-price-test python -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health')); assert data['model_loaded'], data"; do
                        attempt=$((attempt + 1))
                        if [ "$attempt" -ge 20 ]; then
                            docker logs flight-price-test
                            exit 1
                        fi
                        sleep 2
                    done
                '''
            }
        }

        stage('Upload image') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASSWORD'
                )]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login --username "$DOCKER_USER" --password-stdin
                        docker push "$IMAGE_NAME:$IMAGE_TAG"
                        docker logout
                    '''
                }
            }
        }

        stage('Deploy') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    sh '''
                        set -eux
                        export PATH="$WORKSPACE/bin:$PATH"

                        if ! command -v kubectl >/dev/null 2>&1; then
                            mkdir -p "$WORKSPACE/bin"
                            curl -fsSL -o "$WORKSPACE/bin/kubectl" "https://dl.k8s.io/release/$(curl -fsSL https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
                            chmod +x "$WORKSPACE/bin/kubectl"
                        fi

                        test -s "$KUBECONFIG"
                        kubectl --kubeconfig "$KUBECONFIG" config view --minify
                        kubectl --kubeconfig "$KUBECONFIG" cluster-info
                        kubectl --kubeconfig "$KUBECONFIG" set image deployment/flight-price-api flight-price-api="$IMAGE_NAME:$IMAGE_TAG"
                        kubectl --kubeconfig "$KUBECONFIG" rollout status deployment/flight-price-api --timeout=120s
                    '''
                }
            }
        }
    }

    post {
        always {
            sh 'docker rm -f flight-price-test || true'
        }
    }
}