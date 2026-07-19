/*
 * Liens Personal Learning Layer
 *
 * Learner-owned state for saved Language Objects, collections, and review
 * events. It deliberately references the read-only canonical graph instead of
 * copying or changing its facts, relationships, or Learning Resources.
 */
(() => {
  const DB_NAME = 'liens-personal-learning';
  const DB_VERSION = 1;
  const ITEMS = 'learning_objects';
  const COLLECTIONS = 'collections';
  const MEMBERSHIPS = 'collection_memberships';
  const REVIEWS = 'review_events';
  const SAVED_COLLECTION_ID = 'system:saved';

  const items = new Map();
  const collections = new Map();
  const memberships = new Map();
  const reviewEvents = new Map();
  let database = null;
  let mode = 'initializing';

  const timestamp = () => new Date().toISOString();
  const today = () => timestamp().slice(0, 10);
  const identifier = () => globalThis.crypto?.randomUUID?.() || `pl_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  const requestAsPromise = request => new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error || new Error('Personal Learning Layer request failed.'));
  });
  const transactionDone = transaction => new Promise((resolve, reject) => {
    transaction.oncomplete = () => resolve();
    transaction.onerror = () => reject(transaction.error || new Error('Personal Learning Layer transaction failed.'));
    transaction.onabort = () => reject(transaction.error || new Error('Personal Learning Layer transaction aborted.'));
  });
  const membershipId = (collectionId, itemId) => `${collectionId}:${itemId}`;
  const defaultCollection = () => ({
    id: SAVED_COLLECTION_ID,
    title: 'Saved',
    description: 'Everything you choose to return to.',
    system: true,
    createdAt: timestamp(),
  });

  const openDatabase = () => {
    if (!globalThis.indexedDB) return Promise.resolve(null);
    return new Promise((resolve, reject) => {
      const request = globalThis.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        const itemStore = db.objectStoreNames.contains(ITEMS)
          ? request.transaction.objectStore(ITEMS)
          : db.createObjectStore(ITEMS, { keyPath: 'id' });
        if (!itemStore.indexNames.contains('targetKey')) itemStore.createIndex('targetKey', 'targetKey', { unique: true });
        if (!itemStore.indexNames.contains('targetType')) itemStore.createIndex('targetType', 'targetType', { unique: false });
        if (!itemStore.indexNames.contains('lastReviewedDay')) itemStore.createIndex('lastReviewedDay', 'lastReviewedDay', { unique: false });
        const collectionStore = db.objectStoreNames.contains(COLLECTIONS)
          ? request.transaction.objectStore(COLLECTIONS)
          : db.createObjectStore(COLLECTIONS, { keyPath: 'id' });
        if (!collectionStore.indexNames.contains('createdAt')) collectionStore.createIndex('createdAt', 'createdAt', { unique: false });
        const membershipStore = db.objectStoreNames.contains(MEMBERSHIPS)
          ? request.transaction.objectStore(MEMBERSHIPS)
          : db.createObjectStore(MEMBERSHIPS, { keyPath: 'id' });
        if (!membershipStore.indexNames.contains('collectionId')) membershipStore.createIndex('collectionId', 'collectionId', { unique: false });
        if (!membershipStore.indexNames.contains('itemId')) membershipStore.createIndex('itemId', 'itemId', { unique: false });
        const reviewStore = db.objectStoreNames.contains(REVIEWS)
          ? request.transaction.objectStore(REVIEWS)
          : db.createObjectStore(REVIEWS, { keyPath: 'id' });
        if (!reviewStore.indexNames.contains('itemId')) reviewStore.createIndex('itemId', 'itemId', { unique: false });
        if (!reviewStore.indexNames.contains('reviewedAt')) reviewStore.createIndex('reviewedAt', 'reviewedAt', { unique: false });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error('Personal Learning Layer could not open.'));
      request.onblocked = () => reject(new Error('Personal Learning Layer upgrade is blocked by another tab.'));
    });
  };

  const write = async (storeName, record) => {
    await ready;
    if (!database) return record;
    const transaction = database.transaction(storeName, 'readwrite');
    transaction.objectStore(storeName).put(record);
    await transactionDone(transaction);
    return record;
  };
  const remove = async (storeName, key) => {
    await ready;
    if (!database) return;
    const transaction = database.transaction(storeName, 'readwrite');
    transaction.objectStore(storeName).delete(key);
    await transactionDone(transaction);
  };
  const ensureSavedCollection = async ({ bootstrap = false } = {}) => {
    if (collections.has(SAVED_COLLECTION_ID)) return collections.get(SAVED_COLLECTION_ID);
    const collection = defaultCollection();
    collections.set(collection.id, collection);
    if (bootstrap && database) {
      const transaction = database.transaction(COLLECTIONS, 'readwrite');
      transaction.objectStore(COLLECTIONS).put(collection);
      await transactionDone(transaction);
    } else {
      await write(COLLECTIONS, collection);
    }
    return collection;
  };
  const addMembership = async (collectionId, itemId) => {
    const record = { id: membershipId(collectionId, itemId), collectionId, itemId, addedAt: timestamp() };
    memberships.set(record.id, record);
    await write(MEMBERSHIPS, record);
    return record;
  };

  const load = async () => {
    try {
      database = await openDatabase();
      if (!database) {
        mode = 'memory-fallback';
        collections.set(SAVED_COLLECTION_ID, defaultCollection());
        return;
      }
      const transaction = database.transaction([ITEMS, COLLECTIONS, MEMBERSHIPS, REVIEWS], 'readonly');
      const [storedItems, storedCollections, storedMemberships, storedReviewEvents] = await Promise.all([
        requestAsPromise(transaction.objectStore(ITEMS).getAll()),
        requestAsPromise(transaction.objectStore(COLLECTIONS).getAll()),
        requestAsPromise(transaction.objectStore(MEMBERSHIPS).getAll()),
        requestAsPromise(transaction.objectStore(REVIEWS).getAll()),
      ]);
      storedItems.forEach(record => record?.id && items.set(record.id, record));
      storedCollections.forEach(record => record?.id && collections.set(record.id, record));
      storedMemberships.forEach(record => record?.id && memberships.set(record.id, record));
      storedReviewEvents.forEach(record => record?.id && reviewEvents.set(record.id, record));
      mode = 'indexeddb';
      await ensureSavedCollection({ bootstrap: true });
    } catch (error) {
      console.warn('Liens Personal Learning Layer is unavailable; using this-session memory only.', error);
      database = null;
      mode = 'memory-fallback';
      collections.set(SAVED_COLLECTION_ID, defaultCollection());
    }
  };

  const ready = load().then(() => globalThis.dispatchEvent?.(new Event('liens-personal-learning-ready')));
  const listItems = () => [...items.values()].sort((left, right) => String(right.createdAt).localeCompare(String(left.createdAt)));
  const listCollections = () => [...collections.values()].sort((left, right) => Number(Boolean(right.system)) - Number(Boolean(left.system)) || String(left.createdAt).localeCompare(String(right.createdAt)));
  const itemForTargetKey = targetKey => listItems().find(item => item.targetKey === targetKey) || null;
  const membershipsForItem = itemId => [...memberships.values()].filter(record => record.itemId === itemId);
  const itemsForCollection = collectionId => {
    const itemIds = new Set([...memberships.values()].filter(record => record.collectionId === collectionId).map(record => record.itemId));
    return listItems().filter(item => itemIds.has(item.id));
  };
  const collectionIdsForItem = itemId => membershipsForItem(itemId).map(record => record.collectionId);

  const saveItem = async input => {
    await ready;
    const targetKey = String(input.targetKey || input.key || '').trim();
    if (!targetKey) throw new Error('A saved learning object needs a stable target key.');
    const existing = itemForTargetKey(targetKey);
    if (existing) return existing;
    const record = {
      id: identifier(),
      targetKey,
      targetType: input.targetType || input.type || 'language_object',
      targetObjectId: input.targetObjectId || input.id || null,
      canonicalOwnerId: input.canonicalOwnerId || null,
      title: String(input.title || ''),
      detail: String(input.detail || ''),
      sourceContext: input.sourceContext || null,
      createdAt: timestamp(),
      updatedAt: timestamp(),
      lastReviewedAt: null,
      lastReviewedDay: null,
      reviewCount: 0,
    };
    items.set(record.id, record);
    await write(ITEMS, record);
    await ensureSavedCollection();
    await addMembership(SAVED_COLLECTION_ID, record.id);
    return record;
  };

  const importLegacy = async legacyItems => {
    await ready;
    const imported = [];
    for (const legacy of Array.isArray(legacyItems) ? legacyItems : []) {
      if (!legacy?.key) continue;
      imported.push(await saveItem({
        targetKey: legacy.key,
        targetType: legacy.type || 'language_object',
        targetObjectId: legacy.id || null,
        title: legacy.title || '',
        detail: legacy.detail || '',
        sourceContext: { migratedFrom: 'liens-saved' },
      }));
    }
    return imported;
  };

  const removeByTargetKey = async targetKey => {
    await ready;
    const item = itemForTargetKey(targetKey);
    if (!item) return false;
    const itemMemberships = membershipsForItem(item.id);
    const events = [...reviewEvents.values()].filter(event => event.itemId === item.id);
    items.delete(item.id);
    itemMemberships.forEach(record => memberships.delete(record.id));
    events.forEach(event => reviewEvents.delete(event.id));
    await remove(ITEMS, item.id);
    await Promise.all(itemMemberships.map(record => remove(MEMBERSHIPS, record.id)));
    await Promise.all(events.map(event => remove(REVIEWS, event.id)));
    return true;
  };

  const createCollection = async ({ title, description = '' }) => {
    await ready;
    const cleanTitle = String(title || '').trim().replace(/\s+/g, ' ');
    if (!cleanTitle) throw new Error('Give the collection a name.');
    const existing = listCollections().find(collection => collection.title.toLocaleLowerCase() === cleanTitle.toLocaleLowerCase());
    if (existing) return existing;
    const record = { id: identifier(), title: cleanTitle, description: String(description || '').trim(), system: false, createdAt: timestamp() };
    collections.set(record.id, record);
    await write(COLLECTIONS, record);
    return record;
  };
  const setCollectionMembership = async ({ collectionId, itemId, enabled }) => {
    await ready;
    if (!collections.has(collectionId) || !items.has(itemId)) return false;
    if (collectionId === SAVED_COLLECTION_ID && !enabled) return false;
    const id = membershipId(collectionId, itemId);
    if (enabled) {
      if (memberships.has(id)) return true;
      await addMembership(collectionId, itemId);
      return true;
    }
    memberships.delete(id);
    await remove(MEMBERSHIPS, id);
    return true;
  };
  const todayItems = (limit = 12) => listItems()
    .filter(item => item.lastReviewedDay !== today())
    .sort((left, right) => {
      if (!left.lastReviewedAt && right.lastReviewedAt) return -1;
      if (left.lastReviewedAt && !right.lastReviewedAt) return 1;
      return String(left.lastReviewedAt || left.createdAt).localeCompare(String(right.lastReviewedAt || right.createdAt));
    })
    .slice(0, limit);
  const recordReview = async ({ itemId, response, promptType }) => {
    await ready;
    const item = items.get(itemId);
    if (!item) return null;
    const reviewedAt = timestamp();
    const event = { id: identifier(), itemId, response, promptType, reviewedAt };
    const updated = { ...item, lastReviewedAt: reviewedAt, lastReviewedDay: reviewedAt.slice(0, 10), reviewCount: Number(item.reviewCount || 0) + 1, updatedAt: reviewedAt };
    items.set(updated.id, updated);
    reviewEvents.set(event.id, event);
    await write(ITEMS, updated);
    await write(REVIEWS, event);
    return event;
  };

  globalThis.LiensPersonalLearningStore = Object.freeze({
    ready: () => ready,
    mode: () => mode,
    savedCollectionId: SAVED_COLLECTION_ID,
    listItems,
    listCollections,
    itemForTargetKey,
    itemsForCollection,
    collectionIdsForItem,
    todayItems,
    saveItem,
    importLegacy,
    removeByTargetKey,
    createCollection,
    setCollectionMembership,
    recordReview,
  });
})();
