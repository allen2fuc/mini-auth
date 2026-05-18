image_name = mini-auth
repo_name = allen2fuc/${image_name}
version = latest

build:
	docker build -t ${repo_name}:${version} .

push: build
	docker push ${repo_name}:${version}