import { openai } from "@ai-sdk/openai";
import { CoreMessage, generateObject, UserContent } from "ai";
import { z } from "zod";
import { ObserveResult, Stagehand } from "@browserbasehq/stagehand";

const LLMClient = openai("gpt-4o");

type Step = {
  text: string;
  reasoning: string;
  tool: "GOTO" | "ACT" | "EXTRACT" | "OBSERVE" | "CLOSE" | "WAIT" | "NAVBACK";
  instruction: string;
};

async function runStagehand({
  sessionID,
  method,
  instruction,
}: {
  sessionID: string;
  method:
    | "GOTO"
    | "ACT"
    | "EXTRACT"
    | "CLOSE"
    | "SCREENSHOT"
    | "OBSERVE"
    | "WAIT"
    | "NAVBACK";
  instruction?: string;
}) {
  const stagehand = new Stagehand({
    browserbaseSessionID: sessionID,
    env: "BROWSERBASE",
    logger: () => {},
  });
  await stagehand.init();

  const page = stagehand.page;

  try {
    switch (method) {
      case "GOTO":
        await page.goto(instruction!, {
          waitUntil: "commit",
          timeout: 60000,
        });
        break;

      case "ACT":
        await page.act(instruction!);
        break;

      case "EXTRACT": {
        const { extraction } = await page.extract(instruction!);
        return extraction;
      }

      case "OBSERVE":
        return await page.observe({
          instruction,
          onlyVisible: true,
        });

      case "CLOSE":
        await stagehand.close();
        break;

      case "SCREENSHOT": {
        const cdpSession = await page.context().newCDPSession(page);
        const { data } = await cdpSession.send("Page.captureScreenshot");
        return data;
      }

      case "WAIT":
        await new Promise((resolve) =>
          setTimeout(resolve, Number(instruction))
        );
        break;

      case "NAVBACK":
        await page.goBack();
        break;
    }
  } catch (error) {
    await stagehand.close();
    throw error;
  }
}

async function sendPrompt({
  goal,
  sessionID,
  previousSteps = [],
  previousExtraction,
}: {
  goal: string;
  sessionID: string;
  previousSteps?: Step[];
  previousExtraction?: string | ObserveResult[];
}) {
  let currentUrl = "";

  try {
    const stagehand = new Stagehand({
      browserbaseSessionID: sessionID,
      env: "BROWSERBASE",
    });
    await stagehand.init();
    currentUrl = await stagehand.page.url();
    await stagehand.close();
  } catch (error) {
    console.error("Error getting page info:", error);
  }

  const content: UserContent = [
    {
      type: "text",
      text: `Consider the following screenshot of a web page${
        currentUrl ? ` (URL: ${currentUrl})` : ""
      }, with the goal being "${goal}".
  ${
    previousSteps.length > 0
      ? `Previous steps taken:
  ${previousSteps
    .map(
      (step, index) => `
  Step ${index + 1}:
  - Action: ${step.text}
  - Reasoning: ${step.reasoning}
  - Tool Used: ${step.tool}
  - Instruction: ${step.instruction}
  `
    )
    .join("\n")}`
      : ""
  }
  Determine the immediate next step to take to achieve the goal. 
  
  Important guidelines:
  1. Break down complex actions into individual atomic steps
  2. For ACT commands, use only one action at a time, such as:
     - Single click on a specific element
     - Type into a single input field
     - Select a single option
  3. Avoid combining multiple actions in one instruction
  4. If multiple actions are needed, they should be separate steps
  
  If the goal has been achieved, return "close".`,
    },
  ];

  // Add screenshot if navigated to a page previously
  if (
    previousSteps.length > 0 &&
    previousSteps.some((step) => step.tool === "GOTO")
  ) {
    content.push({
      type: "image",
      image: (await runStagehand({
        sessionID,
        method: "SCREENSHOT",
      })) as string,
    });
  }

  if (previousExtraction) {
    content.push({
      type: "text",
      text: `The result of the previous ${
        Array.isArray(previousExtraction) ? "observation" : "extraction"
      } is: ${previousExtraction}.`,
    });
  }

  const message: CoreMessage = {
    role: "user",
    content,
  };

  const result = await generateObject({
    model: LLMClient,
    schema: z.object({
      text: z.string(),
      reasoning: z.string(),
      tool: z.enum([
        "GOTO",
        "ACT",
        "EXTRACT",
        "OBSERVE",
        "CLOSE",
        "WAIT",
        "NAVBACK",
      ]),
      instruction: z.string(),
    }),
    messages: [message],
  });

  return {
    result: result.object,
    previousSteps: [...previousSteps, result.object],
  };
}

async function selectStartingUrl(goal: string) {
  const message: CoreMessage = {
    role: "user",
    content: [
      {
        type: "text",
        text: `Given the goal: "${goal}", determine the best URL to start from.
  Choose from:
  1. A relevant search engine (Google, Bing, etc.)
  2. A direct URL if you're confident about the target website
  3. Any other appropriate starting point
  
  Return a URL that would be most effective for achieving this goal.`,
      },
    ],
  };

  const result = await generateObject({
    model: LLMClient,
    schema: z.object({
      url: z.string().url(),
      reasoning: z.string(),
    }),
    messages: [message],
  });

  return result.object;
}


async function runAgent() {
    const stagehand = new Stagehand();
    await stagehand.init();


    const goal = "Do 5-year historical revenue and debt analysis on Microsoft"
    const sessionId: string = "xyz"
    const previousSteps: Step[] = []

    // get next action
    const { result, previousSteps: newPreviousSteps } = await sendPrompt({
        goal,
        sessionID: sessionId,
        previousSteps,
    });

    if (result.tool == "CLOSE") {
        // we're done exit look maybe
    }

    // const step = null

    // const extraction = await runStagehand({
    //     sessionID: sessionId,
    //     method: step.tool,
    //     instruction: step.instruction
    // })
}