#/bin/bash
cmd=$1

if [ ${cmd} == "to_geotiff" ]; then
	product_id=$(echo $2 | cut -f 2 -d =)
	./procesar.sh ${product_id}
fi

if [ ${cmd} == "to_geotiff_multiple" ]; then
	query=$(echo $2 | cut -f 2-30 -d =)
	url="http://localhost:8080/api/v1/products/?type=csv.latlon&${query}"
	echo "url: ${url}"
	ids=$(curl ${url} | egrep -o "[0-9a-z]{24}")
	echo "IDS: ${ids}"
	for id in ${ids}; do
		echo Procesando ${id}...
		./procesar.sh ${id}
	done
fi