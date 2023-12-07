import dotenv from 'dotenv'
import fs from 'fs'
import http from 'http'
import { Octokit, App } from 'octokit'
import { createNodeMiddleware } from '@octokit/webhooks'

// Load environment variables from .env file
dotenv.config()

// Set configured values
const appId = process.env.APP_ID
const privateKeyPath = process.env.PRIVATE_KEY_PATH
const privateKey = fs.readFileSync(privateKeyPath, 'utf8')
const secret = process.env.WEBHOOK_SECRET
const enterpriseHostname = process.env.ENTERPRISE_HOSTNAME
const messageForNewPRs = fs.readFileSync('./message.md', 'utf8')

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

async function pullRequestHasRelevantChanges(octokit, repository, pull_request) {
  // Get the files altered in the pull request
  const files = await octokit.rest.pulls.listFiles({
    owner: repository.owner.login,
    repo: repository.name,
    pull_number: pull_request.number,
  })

  // Show file names (debug)
  files.data.forEach(file => console.log(file.filename))

  // Check if the pull request contains a relevant file
  const hasRelevantChanges = files.data.some(file => file.filename.toLowerCase() === 'readme.md')
  console.log("Contains " + (hasRelevantChanges ? "" : "no ") + "relevant files")
  return hasRelevantChanges
}

async function pullRequestAltered(octokit, repository, pull_request) {
  const hasRelevantChanges = await pullRequestHasRelevantChanges(octokit, repository, pull_request)

  if (hasRelevantChanges) {
    try {
      await octokit.rest.checks.create({
        owner: repository.owner.login,
        repo: repository.name,
        name: 'Example Check Suite',
        head_sha: pull_request.head.sha,
        status: 'in_progress',
      })
    } catch (error) {
      if (error.response) {
        console.error(`Error! Status: ${error.response.status}. Message: ${error.response.data.message}`)
      } else {
        console.error(error)
      }
    }

    // Wait 10 seconds, simulate logic
    await new Promise(r => setTimeout(r, 10000))

    try {
      await octokit.rest.checks.create({
        owner: repository.owner.login,
        repo: repository.name,
        name: 'Example Check Suite',
        head_sha: pull_request.head.sha,
        status: 'completed',
        conclusion: 'failure',
      })
    } catch (error) {
      if (error.response) {
        console.error(`Error! Status: ${error.response.status}. Message: ${error.response.data.message}`)
      } else {
        console.error(error)
      }
    }
  }
}

// Subscribe to the "pull_request.opened" webhook event
app.webhooks.on('pull_request.opened', async ({ octokit, payload }) => {
  console.log(`Received a pull request opened event for #${payload.pull_request.number}`)

  pullRequestAltered(octokit, payload.repository, payload.pull_request)
})

// Subscribe to the "pull_request.synchronize" webhook event
app.webhooks.on('pull_request.synchronize', async ({ octokit, payload }) => {
  console.log(`Received a pull request synchronize event for #${payload.pull_request.number}`)

  pullRequestAltered(octokit, payload.repository, payload.pull_request)
})

// Subscribe to the "check_suite.rerequested" webhook event
app.webhooks.on('check_suite.rerequested', async ({ octokit, payload }) => {
  console.log(`Received a check suite rerequested event for #${payload.check_suite.id}`)

  payload.check_suite.pull_requests.forEach(pull_request => {
    pullRequestAltered(octokit, payload.repository, pull_request)
  })
})

// Subscribe to the "check_run.rerequested" webhook event
app.webhooks.on('check_run.rerequested', async ({ octokit, payload }) => {
  console.log(`Received a check run rerequested event for #${payload.check_run.id}`)

  payload.check_run.pull_requests.forEach(pull_request => {
    pullRequestAltered(octokit, payload.repository, pull_request)
  })
})

// Subscribe to the "issue_comment.created" webhook event
app.webhooks.on('issue_comment.created', async ({ octokit, payload }) => {
  console.log(`Received an issue comment created event for #${payload.issue.number}`)

  // Check if the comment is on a pull request
  if (payload.issue.pull_request) {
    // Check if the comment contains the magic phrase
    if (payload.comment.body.toLowerCase().includes('please unblock')) {
      // Post a comment on the pull request
      try {
        const { data: pullRequest } = await octokit.rest.pulls.get({
          owner: payload.repository.owner.login,
          repo: payload.repository.name,
          pull_number: payload.issue.number,
        });

        // Extract the head SHA from the pull request
        const headSha = pullRequest.head.sha;

        await octokit.rest.checks.create({
          owner: payload.repository.owner.login,
          repo: payload.repository.name,
          name: 'Example Check Suite',
          head_sha: headSha,
          status: 'completed',
          conclusion: 'success',
        })
      } catch (error) {
        if (error.response) {
          console.error(`Error! Status: ${error.response.status}. Message: ${error.response.data.message}`)
        } else {
          console.error(error)
        }
      }
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
const port = process.env.PORT || 3000
const path = '/api/webhook'
const localWebhookUrl = `http://localhost:${port}${path}`

// See https://github.com/octokit/webhooks.js/#createnodemiddleware for all options
const middleware = createNodeMiddleware(app.webhooks, { path })

http.createServer(middleware).listen(port, () => {
  console.log(`Server is listening for events at: ${localWebhookUrl}`)
  console.log('Press Ctrl + C to quit.')
})
