// import * as serverlessExpress from "@vendia/serverless-express";
import { Context, APIGatewayEvent } from 'aws-lambda';

import * as dotenv from "dotenv";

import * as crypto from "crypto";
import { App } from "@octokit/app";
import { OAuthApp, createAWSLambdaAPIGatewayV2Handler } from "@octokit/oauth-app";
import { Webhooks, createNodeMiddleware } from "@octokit/webhooks";
import { Octokit } from "@octokit/rest";
import { Config } from "sst/node/config";
import { message } from "./message";

dotenv.config()

//@ts-ignore
const appId = Config.APP_ID
//@ts-ignore
// const privateKey = Buffer.from(Config.GITHUB_PRIVATE_KEY, 'utf-8').toString()

//@ts-ignore
// const privateKey = crypto.createPrivateKey(Config.GITHUB_PRIVATE_KEY).export({
//   type: "pkcs8",
//   format: "pem",
// })

//@ts-ignore
const messageForNewPRs = Buffer.from(message, 'utf-8').toString()

// const privateKey = Buffer.from(Config.GITHUB_PRIVATE_KEY, 'utf-8').toString()
const privateKey = process.env.GITHUB_PRIVATE_KEY

// const enterpriseHostname = process.env.ENTERPRISE_HOSTNAME

// Create an authenticated Octokit client authenticated as a GitHub App
const app = new App({
  appId,
  privateKey,
  oauth: {
    clientId: "Iv1.211cf3a1613c44e1",
    clientSecret: "136c619b6306e8358b2f90102b1ba96f4e7ba9b5",
  },
  // ...(enterpriseHostname && {
  //   Octokit: Octokit.defaults({
  //     baseUrl: `https://${enterpriseHostname}/api/v3`
  //   })
  // })
})

// const app = new OAuthApp({
//   clientType: "github-app",
//   clientId: "Iv1.211cf3a1613c44e1",
//   clientSecret: "136c619b6306e8358b2f90102b1ba96f4e7ba9b5",
// });

// Subscribe to the "pull_request.opened" webhook event

const webhooks = new Webhooks({
  secret: "this-is-the-best-app",
})

webhooks.on('pull_request.opened', async ({ payload }) => {
  console.log(`Received a pull request event for #${payload.pull_request.number}`)
  // Create an authenticated Octokit client instance

  // Obtain the installation access token
  const installation = await app.getInstallationOctokit(payload.installation.id);
  const octokit = new Octokit({
    auth: installation,
  });

  try {
    await octokit.rest.issues.createComment({
      owner: payload.repository.owner.login,
      repo: payload.repository.name,
      issue_number: payload.pull_request.number,
      body: messageForNewPRs
    })
  } catch (error) {
    if (error.response) {
      console.error(`Error! Status: ${error.response.status}. Message: ${error.response.data.message}`)
    } else {
      console.error(error)
    }
    console.error(error)
  }
})

// Optional: Handle errors
webhooks.onError((error) => {
  if (error.name === 'AggregateError') {
    // Log Secret verification errors
    console.log(`Error processing request: ${error.event}`)
  } else {
    console.log(error)
  }
})

export const handler = async (event: APIGatewayEvent) => {
  try {
    const webhookEvent = JSON.parse(event.body);
    console.log(webhookEvent)

    console.log(event.headers)

    // Verify and process the webhook event
    await webhooks.verifyAndReceive({
      id: event.headers['x-github-delivery'],
      name: event.headers['x-github-event'],
      signature: event.headers['x-hub-signature-256'],
      payload: webhookEvent,
    });

    return { statusCode: 200, body: 'Success' };
  } catch (error) {
    console.error(error);
    return { statusCode: 500, body: 'Error' };
  }
}