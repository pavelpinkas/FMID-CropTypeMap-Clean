#!/bin/bash 

declare -r GS_BUCKET="gs://agros-data-products/FMID/CTM2021/September"
# declare -r GS_BUCKET="gs://agros-data-products/FMID/CTM2021/August"
# declare -r GS_BUCKET="gs://agros-data-products/FMID/CTM2021/July"

declare -ra AUTHORIZED_USERS=( "fmidapps@gmail.com"      \
                               "pinkasp@gmail.com"       \
                               "jorczyko@gmail.com"      \
                               "mutlu@agrograph.com"     \
                               "lexie@agrograph.com" )

objects=$(gsutil ls $GS_BUCKET/*.tif)

for obj in ${objects[@]} ;  do 
    echo $obj

    for user in ${AUTHORIZED_USERS[@]} ; do 
        gsutil acl ch -u $user":R" $obj 
    done 
done 

