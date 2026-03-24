import { createClient } from "@supabase/supabase-js";

const SUPABASE_URL = process.env.SUPABASE_URL || process.env.REACT_APP_SUPABASE_URL;
const SUPABASE_SERVICE_ROLE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_ROLE_KEY) {
  console.error(
    "Missing env vars. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY before running."
  );
  process.exit(1);
}

const dryRun = process.argv.includes("--dry-run");
const keepArg = process.argv.find((arg) => arg.startsWith("--keep="));
const keepEmails = new Set(
  keepArg
    ? keepArg
        .replace("--keep=", "")
        .split(",")
        .map((email) => email.trim().toLowerCase())
        .filter(Boolean)
    : []
);

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function listAllUsers() {
  const users = [];
  let page = 1;
  const perPage = 1000;

  while (true) {
    const { data, error } = await supabase.auth.admin.listUsers({
      page,
      perPage,
    });
    if (error) throw error;

    const pageUsers = data?.users || [];
    users.push(...pageUsers);

    if (pageUsers.length < perPage) break;
    page += 1;
  }

  return users;
}

async function main() {
  const users = await listAllUsers();
  const toDelete = users.filter((u) => {
    const email = (u.email || "").toLowerCase();
    return email && !keepEmails.has(email);
  });

  console.log(`Found ${users.length} auth user(s).`);
  console.log(`Targeting ${toDelete.length} user(s) for deletion.`);
  if (keepEmails.size > 0) {
    console.log(`Keeping: ${Array.from(keepEmails).join(", ")}`);
  }

  for (const user of toDelete) {
    const label = `${user.email || "no-email"} (${user.id})`;
    if (dryRun) {
      console.log(`[dry-run] would delete ${label}`);
      continue;
    }

    const { error } = await supabase.auth.admin.deleteUser(user.id);
    if (error) {
      console.error(`Failed to delete ${label}: ${error.message}`);
      continue;
    }
    console.log(`Deleted ${label}`);
  }

  console.log("Done.");
}

main().catch((err) => {
  console.error("Reset failed:", err.message || err);
  process.exit(1);
});
