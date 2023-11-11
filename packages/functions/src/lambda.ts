const serverlessExpress = require("@vendia/serverless-express")
const middleware = require("../../../app")

export const handler = serverlessExpress({ middleware });
