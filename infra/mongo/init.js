// Market Lion — MongoDB Initialization
db = db.getSiblingDB('market_lion_news');

// News articles collection
db.createCollection('news_articles');
db.news_articles.createIndex({ published_at: -1 });
db.news_articles.createIndex({ symbols: 1, published_at: -1 });
db.news_articles.createIndex({ sentiment_score: 1 });
db.news_articles.createIndex({ source: 1 });
// TTL: delete articles older than 30 days
db.news_articles.createIndex({ published_at: 1 }, { expireAfterSeconds: 2592000 });

// Twitter/X leader tweets
db.createCollection('leader_tweets');
db.leader_tweets.createIndex({ created_at: -1 });
db.leader_tweets.createIndex({ symbols: 1 });
db.leader_tweets.createIndex({ author_handle: 1 });

// Economic events (ForexFactory, FRED, etc.)
db.createCollection('economic_events');
db.economic_events.createIndex({ event_date: 1 });
db.economic_events.createIndex({ currency: 1, event_date: 1 });
db.economic_events.createIndex({ impact: 1 });

// COT Reports (CFTC)
db.createCollection('cot_reports');
db.cot_reports.createIndex({ report_date: -1 });
db.cot_reports.createIndex({ asset: 1, report_date: -1 });

// Fundamental snapshots
db.createCollection('fundamental_snapshots');
db.fundamental_snapshots.createIndex({ symbol: 1, generated_at: -1 });
db.fundamental_snapshots.createIndex({ generated_at: 1 }, { expireAfterSeconds: 86400 });

// Signal notifications log
db.createCollection('notification_log');
db.notification_log.createIndex({ user_id: 1, sent_at: -1 });
db.notification_log.createIndex({ channel: 1 });
db.notification_log.createIndex({ sent_at: 1 }, { expireAfterSeconds: 604800 });

print('MongoDB Market Lion initialized successfully');
