import { supabase } from "./supabaseClient.js";

/**
 * Fetches all RFP entries from the "RFPs" table in Supabase
 * and returns a list of dictionaries formatted like cardsData.
 */
export async function fetchRFPs() {
  const { data, error } = await supabase
    .from("RFPs")
    .select("id")
    .order("id", { ascending: true });

  if (error) {
    console.error("❌ Error fetching RFPs:", error);
    return [];
  }

  const formatted = data.map((row) => ({
    id: row.id,
    title: `RFP ${row.id}`,
  }));
  console.log(formatted)
  return formatted;
}
