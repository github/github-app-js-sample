import { StackContext, Api, EventBus } from "sst/constructs";

export function API({ stack }: StackContext) {
  const api = new Api(stack, "api", {
    routes: {
      "POST /": "packages/functions/src/lambda.handler",
    },
  });

  stack.addOutputs({
    CustomUrl: api.customDomainUrl,
    ApiEndpoint: api.url,
  });
}
