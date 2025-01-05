CREATE TABLE "sessions" (
  "id" bigint PRIMARY KEY,
  "session_id" varchar,
  "create_time" timestamp
);

CREATE TABLE "users" (
  "id" integer PRIMARY KEY,
  "username" varchar,
  "source" varchar,
  "create_time" timestamp
);

CREATE TABLE "images" (
  "id" bigint PRIMARY KEY,
  "path" varchar,
  "creator_id" integer,
  "device_id" integer,
  "location" wkt,
  "taken_time" timestamp,
  "focus_35mm" integer,
  "orientation_from_north" float,
  "other_metadata" json
);

CREATE TABLE "transcripts" (
  "id" bigint PRIMARY KEY,
  "text" varchar
);

CREATE TABLE "devices" (
  "id" integer PRIMARY KEY,
  "device_maker" varchar,
  "device_model" varchar
);

CREATE TABLE "embeddings" (
  "id" bigint PRIMARY KEY,
  "image_id" bigint,
  "transcript_id" bigint,
  "image_embedding" vector,
  "text_embedding" vector
);

COMMENT ON COLUMN "embeddings"."image_embedding" IS 'embedding of the image';

COMMENT ON COLUMN "embeddings"."text_embedding" IS 'embedding of the transcript';

ALTER TABLE "images" ADD FOREIGN KEY ("creator_id") REFERENCES "users" ("id");

ALTER TABLE "images" ADD FOREIGN KEY ("device_id") REFERENCES "devices" ("id");

ALTER TABLE "embeddings" ADD FOREIGN KEY ("image_id") REFERENCES "images" ("id");

ALTER TABLE "embeddings" ADD FOREIGN KEY ("transcript_id") REFERENCES "transcripts" ("id");
