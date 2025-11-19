import React, { useMemo, useState } from 'react';
import { Flashcard } from '../services/apiService';

interface FlashcardDeckProps {
  cards: Flashcard[];
  onDeleteCard?: (cardId: string) => void;
  emptyLabel?: string;
  compact?: boolean;
}

const cardBaseClasses =
  'relative w-full h-40 sm:h-48 cursor-pointer transition-all duration-500';

export const FlashcardDeck: React.FC<FlashcardDeckProps> = ({
  cards,
  onDeleteCard,
  emptyLabel = 'Flashcards will appear here once generated.',
  compact = false,
}) => {
  const [flipped, setFlipped] = useState<Record<string, boolean>>({});

  const sortedCards = useMemo(() => {
    return [...cards].sort((a, b) =>
      (a.topic || '').localeCompare(b.topic || '')
    );
  }, [cards]);

  const toggleCard = (cardId: string) => {
    setFlipped((prev) => ({
      ...prev,
      [cardId]: !prev[cardId],
    }));
  };

  if (!sortedCards.length) {
    return (
      <div className="border border-dashed border-gray-300 rounded-lg p-4 text-center text-gray-500 text-sm">
        {emptyLabel}
      </div>
    );
  }

  return (
    <div
      className={`grid gap-4 ${
        compact ? 'grid-cols-1' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'
      }`}
    >
      {sortedCards.map((card) => {
        const isFlipped = !!flipped[card.id];
        return (
          <div
            key={card.id}
            className="bg-white/70 border border-orange-100 rounded-xl shadow-sm overflow-hidden relative"
          >
            <div
              className={cardBaseClasses}
              style={{ perspective: '1200px' }}
              onClick={() => toggleCard(card.id)}
            >
              <div
                className="absolute inset-0 transition-transform duration-500"
                style={{
                  transformStyle: 'preserve-3d',
                  transform: isFlipped ? 'rotateY(180deg)' : 'rotateY(0deg)',
                }}
              >
                <div
                  className="absolute inset-0 p-4 flex flex-col justify-between"
                  style={{ backfaceVisibility: 'hidden' as const }}
                >
                  <div>
                    <p className="text-xs uppercase tracking-wide text-orange-500 font-semibold">
                      Definition
                    </p>
                    <p className="text-sm text-gray-800 mt-2 line-clamp-6 leading-relaxed">
                      {card.definition}
                    </p>
                  </div>
                  <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                    <span>{card.topic}</span>
                    <span>{card.source === 'manual' ? 'Manual' : 'AI'}</span>
                  </div>
                </div>
                <div
                  className="absolute inset-0 p-4 bg-orange-600 text-white flex flex-col justify-between"
                  style={{
                    backfaceVisibility: 'hidden' as const,
                    transform: 'rotateY(180deg)',
                  }}
                >
                  <div>
                    <p className="text-xs uppercase tracking-wide opacity-80">
                      Term
                    </p>
                    <p className="text-lg font-semibold mt-2">{card.term}</p>
                  </div>
                  <p className="text-sm text-orange-100">{card.topic}</p>
                </div>
              </div>
            </div>
            {onDeleteCard && card.source === 'manual' && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  onDeleteCard(card.id);
                }}
                className="absolute top-2 right-2 text-xs text-red-500 bg-white/80 rounded-full px-2 py-0.5 shadow"
              >
                Remove
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
};
