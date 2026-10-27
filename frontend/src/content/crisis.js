// Static crisis resources. CrisisPanel.vue imports only this file:
// no fetch, no await, no backend or model (AGENTS.md rule 1).

export const CRISIS = {
  title: 'Crisis support',
  intro: 'If you might be in danger or need to talk to someone now:',
  resources: [
    { name: '988 Suicide & Crisis Lifeline', detail: 'Call or text 988', links: [{ label: 'Call 988', href: 'tel:988' }, { label: 'Text 988', href: 'sms:988' }] },
    { name: 'Crisis Text Line', detail: 'Text HOME to 741741', links: [{ label: 'Text HOME to 741741', href: 'sms:741741?&body=HOME' }] },
    { name: 'Emergency', detail: 'Call 911', links: [{ label: 'Call 911', href: 'tel:911' }] },
  ],
  notes: [
    'These resources are for the United States.',
    "This app is a coursework prototype and can't help in a crisis. Nobody monitors it.",
  ],
  back: 'Back to where I was',
}
