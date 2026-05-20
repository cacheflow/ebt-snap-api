create table if not exists stores (
  id bigint generated always as identity primary key,
  record_id bigint unique,
  store_name text,
  store_street_address text,
  additional_address text,
  city text,
  state text,
  zip_code text,
  zip4 text,
  county text,
  store_type text,
  latitude double precision,
  longitude double precision,
  incentive_program text,
  grantee_name text,
  object_id bigint
);

create index if not exists stores_state_idx on stores (state);
create index if not exists stores_city_idx on stores (city);
create index if not exists stores_zip_idx on stores (zip_code);
create index if not exists stores_type_idx on stores (store_type);
