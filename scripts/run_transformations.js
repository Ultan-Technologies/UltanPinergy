
//process.env.AWS_ACCESS_KEY_ID="";
//process.env.AWS_SECRET_ACCESS_KEY="";
//process.env.AWS_DEFAULT_REGION="";

const bucket = "mmbackuppinergy";
const prefix = "Archive";
const lambdaArn = "arn:aws:lambda:eu-west-1:165244625891:function:MM_transform";

const aws = require('aws-sdk');

const s3 = new aws.S3();

aws.config.update({region: process.env.AWS_DEFAULT_REGION});
const lambda = new aws.Lambda();

processBucket(bucket, prefix);

async function processBucket(bucket, prefix, marker = null) {
    let isTruncated = true;
    let totalcount = 0;

    while (isTruncated) {
        let params = { 
            Bucket: bucket, 
            Prefix: prefix
        };
        if (marker) params.Marker = marker;
        const response = await s3.listObjects(params).promise();

        console.log(`Fetched next batch of ${response.Contents.length} items`);

        totalcount += response.Contents.length;

        for (var i in response.Contents) {
            const item = response.Contents[i];
            
            const arguments = {
                Records: [{
                    s3: {
                        object: {
                            key: item.Key,
                        },
                        bucket: {
                            name: bucket
                        }
                    }
                }]
            };
            try {
                const params = {
                    FunctionName: lambdaArn, 
                    InvocationType: "Event",
                    Payload: JSON.stringify(arguments),
                };
                lambda.invoke(params, function(err) {
                    if (err) console.log(err, err.stack);
                });
                await wait(10);
            }
            catch (e) {
                console.error(e, e.stack);
            }
        };

        isTruncated = response.IsTruncated;
        if (isTruncated) {
          marker = response.Contents.slice(-1)[0].Key;
        }
    }
    console.log("Total count: ", totalcount);
}

function wait(timeout) {
    return new Promise((resolve) => setTimeout(resolve, timeout));
}