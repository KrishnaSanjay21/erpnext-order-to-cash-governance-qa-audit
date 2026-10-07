let
    Source = Parquet.Document(File.Contents(DataRoot & "\fact_control_failures.parquet")),
    Types = Table.TransformColumnTypes(Source, {{"month", type date}, {"control_id", type text}, {"failed_rows", Int64.Type}})
in
    Types

