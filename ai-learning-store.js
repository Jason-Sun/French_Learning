/*
 * Liens AI Learning Database
 *
 * A learner-scoped IndexedDB store for AI Learning Resources. It is deliberately
 * separate from the canonical SQLite Language Graph: records here are drafts,
 * never Language Objects, Facts, Evidence, or graph relationships.
 */
(() => {
  const DB_NAME = 'liens-ai-learning';
  const DB_VERSION = 1;
  const RESOURCES = 'learning_resources';
  const RECENTS = 'recent_lookups';

  const resources = new Map();
  const recents = new Map();
  let database = null;
  let mode = 'initializing';

  const requestAsPromise = request => new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('AI Learning Database request failed.'));
  });

  const transactionDone = transaction => new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error || new Error('AI Learning Database transaction failed.'));
    transaction.onabort = () => reject(transaction.error || new Error('AI Learning Database transaction aborted.'));
  });

  const openDatabase = () => {
    if (!globalThis.indexedDB) return Promise.resolve(null);
    return new Promise((resolve, reject) => {
      const request = globalThis.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        const resourceStore = db.objectStoreNames.contains(RESOURCES)
          ? request.transaction.objectStore(RESOURCES)
          : db.createObjectStore(RESOURCES, { keyPath: 'id' });
        if (!resourceStore.indexNames.contains('resourceKey')) resourceStore.createIndex('resourceKey', 'resourceKey', { unique: false });
        if (!resourceStore.indexNames.contains('targetId')) resourceStore.createIndex('targetId', 'targetId', { unique: false });
        if (!resourceStore.indexNames.contains('queryNormalized')) resourceStore.createIndex('queryNormalized', 'queryNormalized', { unique: false });
        if (!resourceStore.indexNames.contains('lifecycle')) resourceStore.createIndex('lifecycle', 'lifecycle', { unique: false });
        const recentStore = db.objectStoreNames.contains(RECENTS)
          ? request.transaction.objectStore(RECENTS)
          : db.createObjectStore(RECENTS, { keyPath: 'normalizedQuery' });
        if (!recentStore.indexNames.contains('lastOpenedAt')) recentStore.createIndex('lastOpenedAt', 'lastOpenedAt', { unique: false });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('AI Learning Database could not open.'));
      request.onblocked = () => reject(new Error('AI Learning Database upgrade is blocked by another tab.'));
    });
  };

  const load = async () => {
    try {
      database = await openDatabase();
      if (!database) {
        mode = 'memory-fallback';
        return;
      }
      const transaction = database.transaction([RESOURCES, RECENTS], 'readonly');
      const [storedResources, storedRecents] = await Promise.all([
        requestAsPromise(transaction.objectStore(RESOURCES).getAll()),
        requestAsPromise(transaction.objectStore(RECENTS).getAll()),
      ]);
      storedResources.forEach(resource => resource?.id && resources.set(resource.id, resource));
      storedRecents.forEach(recent => recent?.normalizedQuery && recents.set(recent.normalizedQuery, recent));
      mode = 'indexeddb';
    } catch (error) {
      console.warn('Liens AI Learning Database is unavailable; using this-session memory only.', error);
      database = null;
      mode = 'memory-fallback';
    }
  };

  const ready = load().then(() => {
    globalThis.dispatchEvent?.(new Event('liens-ai-learning-store-ready'));
  });

  const persistResource = async resource => {
    resources.set(resource.id, resource);
    await ready;
    if (!database) return resource;
    const transaction = database.transaction(RESOURCES, 'readwrite');
    transaction.objectStore(RESOURCES).put(resource);
    await transactionDone(transaction);
    return resource;
  };

  const persistRecent = async recent => {
    recents.set(recent.normalizedQuery, recent);
    await ready;
    if (!database) return recent;
    const transaction = database.transaction(RECENTS, 'readwrite');
    transaction.objectStore(RECENTS).put(recent);
    await transactionDone(transaction);
    return recent;
  };

  const deleteByResourceKey = async resourceKey => {
    [...resources.values()].filter(resource => resource.resourceKey === resourceKey).forEach(resource => resources.delete(resource.id));
    await ready;
    if (!database) return;
    const transaction = database.transaction(RESOURCES, 'readwrite');
    const index = transaction.objectStore(RESOURCES).index('resourceKey');
    const request = index.openCursor(IDBKeyRange.only(resourceKey));
    request.onsuccess = () => {
      const cursor = request.result;
      if (!cursor) return;
      cursor.delete();
      cursor.continue();
    };
    await transactionDone(transaction);
  };

  const listResources = () => [...resources.values()];
  const listRecent = () => [...recents.values()].sort((left, right) => String(right.lastOpenedAt).localeCompare(String(left.lastOpenedAt)));

  globalThis.LiensAILearningStore = Object.freeze({
    ready: () => ready,
    mode: () => mode,
    listResources,
    listRecent,
    putResource: persistResource,
    putRecent: persistRecent,
    deleteByResourceKey,
  });
})();
