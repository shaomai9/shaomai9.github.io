import os

import uvicorn


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("FC_SERVER_PORT", "9000")))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
