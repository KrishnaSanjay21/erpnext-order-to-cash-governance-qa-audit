let
    Source = Parquet.Document(File.Contents(DataRoot & "\fact_monthly_disposition.parquet")),
    Types = Table.TransformColumnTypes(Source, {{"month", type date}, {"record_status", type text}, {"document_type", type text}, {"rows", Int64.Type}, {"documents", Int64.Type}, {"net_revenue_gbp", Currency.Type}})
in
    Types

