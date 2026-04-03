import { Injectable, signal } from '@angular/core';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messages: Message[];
}

const SAMPLE_CONVERSATIONS: Conversation[] = [
  {
    id: '1',
    title: 'Luxury Condos in Manhattan',
    lastMessage: 'Found 12 listings matching your criteria...',
    timestamp: new Date(Date.now() - 1000 * 60 * 30),
    messages: [
      { id: 'm1', role: 'user', content: 'Show me luxury condos in Manhattan under $3M', timestamp: new Date(Date.now() - 1000 * 60 * 32) },
      { id: 'm2', role: 'assistant', content: 'I found 12 luxury condos in Manhattan under $3M. Top picks include a stunning 2BR on the Upper West Side at $2.8M with Central Park views, and a modern 3BR in Tribeca at $2.95M with a private terrace. Would you like detailed information on any of these?', timestamp: new Date(Date.now() - 1000 * 60 * 30) }
    ]
  },
  {
    id: '2',
    title: 'Suburban Family Homes',
    lastMessage: 'Great schools and spacious yards in Westchester...',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3),
    messages: [
      { id: 'm3', role: 'user', content: 'I need a 4 bedroom home with a yard, good schools', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3.1) },
      { id: 'm4', role: 'assistant', content: 'Great schools and spacious yards in Westchester are your best bet! I recommend looking at Scarsdale, Bronxville, and Larchmont. Average 4BR homes range from $1.2M–$2.5M. Shall I narrow it down by school district rating or commute time to the city?', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 3) }
    ]
  },
  {
    id: '3',
    title: 'Investment Properties Brooklyn',
    lastMessage: 'Multi-family units with strong rental yields...',
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24),
    messages: [
      { id: 'm5', role: 'user', content: 'What are good investment properties in Brooklyn?', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24.1) },
      { id: 'm6', role: 'assistant', content: 'Multi-family units in Bushwick, Crown Heights, and Flatbush offer strong rental yields of 5–7% cap rates. I have several 2–4 unit buildings listed between $800K–$1.8M. Would you like me to run the numbers on rental income projections?', timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24) }
    ]
  }
];

const BOT_RESPONSES = [
  "I've searched our database and found several properties that match your criteria. The market in that area is quite active right now, with average listing times of just 18 days.",
  "Based on your preferences, I recommend exploring listings in that neighborhood. Property values have appreciated 8.3% year-over-year, making it an excellent investment opportunity.",
  "I can schedule viewings for any of these properties at your convenience. Our partner agents are available weekdays and weekends. Which listings interest you most?",
  "The property at that price point typically includes HOA fees ranging from $400–$800/month. Would you like me to filter by total monthly cost instead?",
  "Great choice of neighborhood! Schools in that district are rated 8–9/10 on GreatSchools. The area also has excellent walkability and public transit access.",
  "I've analyzed comparable sales in the past 90 days. Based on current market conditions, that listing appears fairly priced. Would you like a full market analysis report?"
];

@Injectable({ providedIn: 'root' })
export class ChatService {
  private _conversations = signal<Conversation[]>(SAMPLE_CONVERSATIONS);
  private _activeConversation = signal<Conversation | null>(null);
  private _isTyping = signal(false);

  conversations = this._conversations.asReadonly();
  activeConversation = this._activeConversation.asReadonly();
  isTyping = this._isTyping.asReadonly();

  selectConversation(id: string) {
    const found = this._conversations().find(c => c.id === id) ?? null;
    this._activeConversation.set(found);
  }

  newConversation() {
    const conv: Conversation = {
      id: crypto.randomUUID(),
      title: 'New Conversation',
      lastMessage: '',
      timestamp: new Date(),
      messages: []
    };
    this._conversations.update(list => [conv, ...list]);
    this._activeConversation.set(conv);
  }

  sendMessage(content: string) {
    if (!content.trim()) return;
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: content.trim(),
      timestamp: new Date()
    };

    this._activeConversation.update(conv => {
      if (!conv) return conv;
      const updated = {
        ...conv,
        messages: [...conv.messages, userMsg],
        lastMessage: content.trim(),
        title: conv.title === 'New Conversation' && conv.messages.length === 0
          ? content.slice(0, 40) + (content.length > 40 ? '...' : '')
          : conv.title,
        timestamp: new Date()
      };
      this._conversations.update(list =>
        list.map(c => c.id === updated.id ? updated : c)
      );
      return updated;
    });

    this._isTyping.set(true);

    setTimeout(() => {
      const botMsg: Message = {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: BOT_RESPONSES[Math.floor(Math.random() * BOT_RESPONSES.length)],
        timestamp: new Date()
      };
      
      this._isTyping.set(false);
      
      this._activeConversation.update(conv => {
        if (!conv) return conv;
        const updated = { ...conv, messages: [...conv.messages, botMsg], lastMessage: botMsg.content, timestamp: new Date() };
        this._conversations.update(list => list.map(c => c.id === updated.id ? updated : c));
        return updated;
      });
    }, 1400 + Math.random() * 800);
  }

  deleteConversation(id: string) {
    this._conversations.update(list => list.filter(c => c.id !== id));
    if (this._activeConversation()?.id === id) {
      const remaining = this._conversations();
      this._activeConversation.set(remaining[0] ?? null);
    }
  }
}