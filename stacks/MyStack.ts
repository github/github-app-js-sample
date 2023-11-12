import { StackContext, Api, Function, Config } from "sst/constructs";

export function API({ stack }: StackContext) {
  const APP_ID = new Config.Secret(stack, "APP_ID")
  const GITHUB_PRIVATE_KEY = new Config.Secret(stack, "GITHUB_PRIVATE_KEY")
  const WEBHOOK_SECRET = new Config.Secret(stack, "WEBHOOK_SECRET")

  const handlerFunc = new Function(stack, "handlerFunc", {
    handler: "packages/functions/src/lambda.handler",
    bind: [APP_ID, GITHUB_PRIVATE_KEY, WEBHOOK_SECRET]
  })

  const api = new Api(stack, "api", {
    customDomain: {
      domainName: process.env.DOMAIN_NAME,
      hostedZone: process.env.HOSTED_ZONE,
    },
    routes: {
      "POST /": handlerFunc,
    },
  });

  stack.addOutputs({
    CustomUrl: api.customDomainUrl,
    ApiEndpoint: api.url,
  });
}
