#创建镜像
docker build -t monkey:v1
#创建容器
docker run -it --rm --name monkey --mount type=bind,source="c:\monkey",target=/usr/src/app/result monkey:v1

