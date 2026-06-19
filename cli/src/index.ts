#!/usr/bin/env node
import { Command } from "commander";
import { runInit } from "./commands/init.js";
import { runInstall } from "./commands/install.js";
import { runBuild } from "./commands/build.js";
import { runStart } from "./commands/start.js";
import { runDev } from "./commands/dev.js";
import { runSetup } from "./commands/setup.js";
import { runDoctor } from "./commands/doctor.js";
import { runStop } from "./commands/stop.js";
import { runLogs } from "./commands/logs.js";
import { runMigrate } from "./commands/migrate.js";
import { runBackup } from "./commands/backup.js";
import { runStatus } from "./commands/status.js";
import { runRegistry } from "./commands/registry.js";
import { runDeploy } from "./commands/deploy.js";
import { runUpdate } from "./commands/update.js";

const program = new Command();

program
  .name("cortex")
  .description("Cortex - AI Agent Workspace CLI")
  .version("1.0.0");

program
  .command("init")
  .description("Initialize a new Cortex workspace")
  .action(runInit);

program
  .command("install")
  .description("Install dependencies and configure services")
  .action(runInstall);

program
  .command("setup")
  .description("Run interactive setup wizard")
  .action(runSetup);

program
  .command("build")
  .description("Build Docker images for all services")
  .action(runBuild);

program
  .command("start")
  .description("Start all Cortex services")
  .option("--profile <name>", "Docker Compose profile to use")
  .option("--detach", "Run in background", true)
  .action(runStart);

program
  .command("dev")
  .description("Start services in development mode with hot reload")
  .option("--profile <name>", "Docker Compose profile to use")
  .action(runDev);

program
  .command("stop")
  .description("Stop all running Cortex services")
  .action(runStop);

program
  .command("status")
  .description("Show status of all running services")
  .option("--json", "Output as JSON")
  .action(runStatus);

program
  .command("doctor")
  .description("Run health checks and diagnose issues")
  .option("--fix", "Attempt to fix issues automatically")
  .action(runDoctor);

program
  .command("logs")
  .description("View logs from services")
  .argument("[service]", "Service name (omit for all)")
  .option("--follow", "Follow log output")
  .option("--lines <n>", "Number of lines to show", "100")
  .action(runLogs);

program
  .command("migrate")
  .description("Run database migrations")
  .argument("[direction]", "Migration direction: up, down, status", "up")
  .action(runMigrate);

program
  .command("backup")
  .description("Create a backup of workspace data")
  .argument("[name]", "Backup name")
  .option("--full", "Include git history")
  .action(runBackup);

program
  .command("deploy")
  .description("Deploy Cortex to production")
  .option("--target <host>", "Deployment target host")
  .option("--env <environment>", "Target environment", "production")
  .action(runDeploy);

program
  .command("update")
  .description("Update Cortex to latest version")
  .action(runUpdate);

program
  .command("registry")
  .description("Manage skill registry")
  .argument("[action]", "Registry action: list, search, install, update", "list")
  .argument("[skill]", "Skill name for install/update")
  .action(runRegistry);

program.parse();
