from scripts.import_stores import clean_row, normalize_header


def test_normalize_header_handles_source_typos() -> None:
    assert normalize_header("Additonal_Address") == "additional_address"
    assert normalize_header("ObjectId") == "object_id"


def test_clean_row_drops_unused_geo_columns_and_casts_values() -> None:
    row = {
        "X": "-118.1",
        "Y": "34.1",
        "Record_ID": "123",
        "Store_Name": " Test Market ",
        "State": "ca",
        "Latitude": "34.0123",
        "Longitude": "-118.0123",
        "ObjectId": "456.0",
        "Zip_Code": "",
    }

    assert clean_row(row) == {
        "record_id": 123,
        "store_name": "Test Market",
        "state": "CA",
        "latitude": 34.0123,
        "longitude": -118.0123,
        "object_id": 456,
        "zip_code": None,
    }
