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