let
    Source = Parquet.Document(File.Contents(DataRoot & "\fact_document_disposition.parquet")),
    Types = Table.TransformColumnTypes(Source, {{"invoice_no", type text}, {"record_status", type text}, {"document_type", type text}, {"invoice_date", type date}, {"lines", Int64.Type}, {"net_revenue_gbp", Currency.Type}, {"country", type text}, {"original_invoice_no", type text}})
in
    Types

