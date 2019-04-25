docker build -t catalog:0 -f Dockerfile.catalog --build-arg id=0 .
docker build -t catalog:1 -f Dockerfile.catalog --build-arg id=1 .
docker build -t frontend:0 -f Dockerfile.catalog --build-arg id=0 .
docker build -t order:0 -f Dockerfile.catalog --build-arg id=0 .
docker build -t order:1 -f Dockerfile.catalog --build-arg id=1 .


