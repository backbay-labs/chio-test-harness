#!/usr/bin/env node
// Minimal stdio MCP server used by the chio smoke-test harness.
//
// Exposes exactly three tools so the chio policy can exercise every guard
// the downstream plugin smoke tests (ST.2.x) depend on:
//
//   echo({msg})            -> {msg}                       // always-allowed happy path
//   delete_file({path})    -> performs fs.unlink(path)    // must trip forbidden_paths
//   paid_action({usd})     -> {charged, receipt_id}       // drives rules.velocity budget
//
// No host globals, no side-effects beyond delete_file. Safe to run as a
// subprocess of `chio mcp serve-http`.

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { unlink } from "node:fs/promises";
import { randomUUID } from "node:crypto";

const TOOLS = [
  {
    name: "echo",
    description: "Echo a message back. Always allowed by the harness policy.",
    inputSchema: {
      type: "object",
      properties: { msg: { type: "string" } },
      required: ["msg"],
      additionalProperties: false,
    },
  },
  {
    name: "delete_file",
    description:
      "Attempt to delete a file on the host. The chio policy's forbidden_paths rule MUST block this.",
    inputSchema: {
      type: "object",
      properties: { path: { type: "string" } },
      required: ["path"],
      additionalProperties: false,
    },
  },
  {
    name: "paid_action",
    description:
      "Simulates a paid action costing {usd} dollars. Drives rules.velocity.max_spend_per_window budget exhaustion.",
    inputSchema: {
      type: "object",
      properties: { usd: { type: "number", minimum: 0 } },
      required: ["usd"],
      additionalProperties: false,
    },
  },
];

const server = new Server(
  { name: "chio-harness-hello-mcp", version: "0.1.0" },
  { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args = {} } = req.params;
  switch (name) {
    case "echo": {
      const msg = String(args.msg ?? "");
      return {
        content: [{ type: "text", text: msg }],
        structuredContent: { msg },
      };
    }
    case "delete_file": {
      const path = String(args.path ?? "");
      try {
        await unlink(path);
        return {
          content: [
            { type: "text", text: `deleted ${path}` },
          ],
          structuredContent: { deleted: true, path },
        };
      } catch (cause) {
        return {
          isError: true,
          content: [
            { type: "text", text: `delete_file failed: ${(cause && cause.message) || String(cause)}` },
          ],
        };
      }
    }
    case "paid_action": {
      const usd = Number(args.usd ?? 0);
      return {
        content: [
          { type: "text", text: `charged ${usd} USD` },
        ],
        structuredContent: {
          charged: usd,
          receipt_id: `paid-${randomUUID()}`,
        },
      };
    }
    default:
      return {
        isError: true,
        content: [{ type: "text", text: `unknown tool ${name}` }],
      };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
