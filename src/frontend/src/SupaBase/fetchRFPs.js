import { supabase } from "./supabaseClient.js";

/**
 * Fetches all RFP entries from the "RFPs" table in Supabase
 * and returns a list of dictionaries formatted like cardsData.
 */
export async function fetchRFPs() {
  // goes to supabase selects the name collumn and creates a row based on names
  const { data, error } = await supabase
    .from("RFPs")
    .select("name, id")
    .order("name", { ascending: true });

  if (error) {
    console.error("❌ Error fetching RFPs:", error);
    return [];
  }

  const formatted = data.map((row) => ({
    id: row.id,
    title: `RFP ${row.name}`,
  }));
  console.log(formatted)
  return formatted;
}
