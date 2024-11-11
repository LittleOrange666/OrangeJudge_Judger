BASEDIR=$(dirname $0)
docker run -p 9132:8000 -v "${BASEDIR}/sandbox":/sandbox --rm judger_server_test