# Kubernetes Commands

Run these commands from the `Flight price prediction` folder.

Your Kubernetes cluster must be running before you begin. The app image is
downloaded automatically from Docker Hub, so Docker Compose is not needed.

## Deploy the app

```bash
kubectl apply -f k8s/
```

## Check the app

```bash
kubectl get pods
kubectl get services
```

Wait until the Pod status is `Running`.

## Open the app locally

```bash
kubectl port-forward service/flight-price-api 8000:8000
```

Open <http://localhost:8000>. Keep this command running while using the app.
Press `Ctrl+C` to stop only the port forwarding.

## Change the number of Pods

Run three copies:

```bash
kubectl scale deployment flight-price-api --replicas=3
```

Run one copy:

```bash
kubectl scale deployment flight-price-api --replicas=1
```

## Temporarily stop the app

```bash
kubectl scale deployment flight-price-api --replicas=0
```

Start it again:

```bash
kubectl scale deployment flight-price-api --replicas=1
```

## Remove the app

```bash
kubectl delete -f k8s/
```
