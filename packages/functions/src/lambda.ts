const serverlessExpress = require("@vendia/serverless-express")
import { middleware } from "../../../app"

export const handler = serverlessExpress({ middleware });
