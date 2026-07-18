import { LeadDetailWorkspace } from "@/components/lead-detail-workspace";

export default async function LeadDetailPage({
  params,
}: Readonly<{ params: Promise<{ leadId: string }> }>) {
  const { leadId } = await params;
  return <LeadDetailWorkspace leadId={leadId} />;
}
