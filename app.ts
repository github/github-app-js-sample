// import dotenv from 'dotenv'
// import http from 'http'

//@ts-ignore
// global.crypto = require('crypto');
import { Octokit, App } from 'octokit'
import { createNodeMiddleware } from '@octokit/webhooks'
import { Config } from "sst/node/config";
import { message } from "./message";

// Load environment variables from .env file
// dotenv.config()

// Set configured values

//@ts-ignore
const appId = Config.APP_ID
//@ts-ignore
const privateKey = Buffer.from(Config.GITHUB_PRIVATE_KEY, 'utf-8').toString()

//@ts-ignore
// const privateKey = crypto.createPrivateKey(Config.GITHUB_PRIVATE_KEY).export({
//   type: "pkcs8",
//   format: "pem",
// })

//@ts-ignore
const secret = Config.WEBHOOK_SECRET
const enterpriseHostname = process.env.ENTERPRISE_HOSTNAME
const messageForNewPRs = Buffer.from(message, 'utf-8').toString()

// Create an authenticated Octokit client authenticated as a GitHub App
const app = new App({
  appId,
  privateKey,
  webhooks: {
    secret
  },
  ...(enterpriseHostname && {
    Octokit: Octokit.defaults({
      baseUrl: `https://${enterpriseHostname}/api/v3`
    })
  })
})

// Optional: Get & log the authenticated app's name
const { data } = await app.octokit.request('/app')

// Read more about custom logging: https://github.com/octokit/core.js#logging
app.octokit.log.debug(`Authenticated as '${data.name}'`)

// Subscribe to the "pull_request.opened" webhook event
app.webhooks.on('pull_request.opened', async ({ octokit, payload }) => {
  console.log(`Received a pull request event for #${payload.pull_request.number}`)
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
  }
})

// Optional: Handle errors
app.webhooks.onError((error) => {
  if (error.name === 'AggregateError') {
    // Log Secret verification errors
    console.log(`Error processing request: ${error.event}`)
  } else {
    console.log(error)
  }
})

// Launch a web server to listen for GitHub webhooks
// const port = process.env.PORT || 3000
const path = '/api/webhook'
// const localWebhookUrl = `http://localhost:${port}${path}`

// See https://github.com/octokit/webhooks.js/#createnodemiddleware for all options
export const middleware = createNodeMiddleware(app.webhooks, { path })

// http.createServer(middleware).listen(port, () => {
//   console.log(`Server is listening for events at: ${localWebhookUrl}`)
//   console.log('Press Ctrl + C to quit.')
// })