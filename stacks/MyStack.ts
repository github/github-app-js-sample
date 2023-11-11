import { StackContext, Api, Function, Config } from "sst/constructs";

export function API({ stack }: StackContext) {
  const GITHUB_PRIVATE_KEY = new Config.Secret(stack, "GITHUB_PRIVATE_KEY")

  const handlerFunc = new Function(stack, "handlerFunc", {
    handler: "packages/functions/src/lambda.handler",
    bind: [GITHUB_PRIVATE_KEY]
  })

  const api = new Api(stack, "api", {
    routes: {
      "POST /": handlerFunc,
    },
  });

  stack.addOutputs({
    CustomUrl: api.customDomainUrl,
    ApiEndpoint: api.url,
  });
}
