class Config:
    DEBUG = True  # Set to False in production

    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:lic-test_2024@localhost/template_postgis_pgvector"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    #SQLALCHEMY_ECHO=True

    SECRET_KEY = "your-secret-key"  # Not needed if no sessions are used
    AZURE_VISION_ENDPOINT = "https://multimodeembeddings.cognitiveservices.azure.com/"
    AZURE_VISION_KEY="ba59f2d86651441886aca24c0dc900bf"
    AZURE_VISION_VERSION = "?api-version=2024-02-01&model-version=2023-04-15"