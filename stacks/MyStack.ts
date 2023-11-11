import { StackContext, Api, Function, Config } from "sst/constructs";

export function API({ stack }: StackContext) {
  const GITHUB_PRIVATE_KEY = new Config.Secret(stack, "GITHUB_PRIVATE_KEY")

  const handlerFunc = new Function(stack, "handlerFunc", {
    handler: "packages/functions/src/lambda.handler",
    bind: [GITHUB_PRIVATE_KEY]
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
