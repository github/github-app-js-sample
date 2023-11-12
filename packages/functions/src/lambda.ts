// import * as serverlessExpress from "@vendia/serverless-express";
import { Context, APIGatewayEvent } from 'aws-lambda';

import * as dotenv from "dotenv";

import * as crypto from "crypto";
import { App } from "@octokit/app";
import { Webhooks } from "@octokit/webhooks";
import { Octokit } from "@octokit/rest";
import { Config } from "sst/node/config";
// import { message } from "./message";

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
// const messageForNewPRs = Buffer.from(message, 'utf-8').toString()

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

webhooks.on('pull_request.opened', async ({ id, name, payload }) => {
  console.log(`Received a pull_request.opened event (id: ${id})`);
  console.log(`Received a pull request event for #${payload.pull_request.number}`)
  // Retrieve the installation ID from the webhook payload
  try {
    const installationId = payload.installation.id;
    // Obtain the installation access token
    const octokit = await app.getInstallationOctokit(installationId);

    await octokit.request(
      "POST /repos/{owner}/{repo}/issues/{issue_number}/comments",
      {
        owner: payload.repository.owner.login,
        repo: payload.repository.name,
        issue_number: payload.pull_request.number,
        body: 'Thank you for your pull request!'
      }
    )
  } catch (error) {
    console.error(`Issue creating comment: ${error}`)
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
    let requestBody = event.body;
    // Decode from base64 if the body is base64 encoded
    if (event.isBase64Encoded && requestBody) {
      requestBody = Buffer.from(requestBody, 'base64').toString('utf-8');
    }

    if (!requestBody) {
      throw new Error('Request body is empty or missing');
    }
    console.log(requestBody)
    console.log(event.headers)

    // Verify and process the webhook event
    await webhooks.verifyAndReceive({
      id: event.headers['x-github-delivery'],
      name: event.headers['x-github-event'],
      signature: event.headers['x-hub-signature-256'],
      payload: requestBody,
    });

    return { statusCode: 200, body: 'Success' };
  } catch (error) {
    console.error(error);
    return { statusCode: 500, body: 'Error' };
  }
}