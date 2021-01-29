## Lambda

`/lambda` contains source code for aws lambda function that transforms XML MM file into JSON format, and puts it into condifured s3 bucket and folder
`default.env` contains the default configuration for the lambda
 - `ARRAY_FIELDS` variable specifies xml filed that should be always treated like arrays. I.e. if the xml looks like this
    ```
    <MIM300_ValidatedNonIntervalReadingsScheduled ...>
        <UsageFactors EstimatedUsageFactor="1404.96126584" EffectiveFromDate="2020-11-10" TimeslotCode="24H"/>
        <UsageFactors EffectiveFromDate="2020-03-17" TimeslotCode="24H" ActualUsageFactor="1732.24617818"/>
    </MIM300_ValidatedNonIntervalReadingsScheduled>
    ```
    we can determine that `UsageFactors` is an array. However if there's only one usage factor:
    ```
    <MIM300_ValidatedNonIntervalReadingsScheduled ...>
        <UsageFactors EstimatedUsageFactor="1404.96126584" EffectiveFromDate="2020-11-10" TimeslotCode="24H"/>
    </MIM300_ValidatedNonIntervalReadingsScheduled>
    ```
    It would be treated as nested object instead of array. In order for the schema to be consinstend across all files, we need to explicitly instruct the transformer to always treat `UsageFactors` as an array.
 - `IGNORE_FIELDS` variable specifies list of fields that are excluded from the resulting json. This includes fields such as `AdditionalAggregationInformation` which contains too disparate data amongst the mm files, and therefore aws services such as Glue and Athena cannot determine a common schema for this field and cannot properly process it.

 ## Scripts
 
 `/scirpts` contains a .js script used to manually trigger the lambda for pre-existing mm files in the bucket. The lambda is set up with a trigger that fires each time a new file appears in the s3 bucket, however to run on the files that have already existed before the trigger was created, a manual invocation is required.

 ## Querying the data

 In order to run a query on the transfomed data, one needs to first run a AWS Glue Crawler on the transformed .json files, in order to generate a virtual table that can be later queried in AWS Athena.
 Curretly, it's already generated and called `mm_json.mm_transformed`.

 Some examples of queries that can be run:

 ```
 --filter by a nested array field 
SELECT *
FROM "mm_json"."mm_transformed"
    CROSS JOIN UNNEST(body_usagefactors) as t(usage_factors)
WHERE header_messagetypecode LIKE '300%'
        AND CAST(usage_factors.ActualUsageFactor AS REAL) > 1700 
ORDER BY CAST(usage_factors.ActualUsageFactor AS REAL)
LIMIT 10

--filter by a nested array count
SELECT *
FROM "mm_json"."mm_transformed"
WHERE cardinality(body_usagefactors) = 1
LIMIT 10

--calculate aggregation on a nested array field
SELECT header_messagetypecode, header_markettimestamp, COUNT(usage_factors)
FROM "mm_json"."mm_transformed"
    CROSS JOIN UNNEST(body_usagefactors) as t(usage_factors)
WHERE header_messagetypecode LIKE '3%'
GROUP BY header_markettimestamp, header_messagetypecode
LIMIT 10

--select a value from a multi-levl nested field
SELECT header_messagetypecode, header_markettimestamp, registerlevelinfo.readingvalue
FROM "mm_json"."mm_transformed"
    CROSS JOIN UNNEST(body_meterid) as t(meterid)
    CROSS JOIN UNNEST(meterid.registerlevelinfo) as t(registerlevelinfo)
WHERE registerlevelinfo IS NOT NULL AND meterid IS NOT NULL AND body_meterid IS NOT NULL
limit 10
 ``` 