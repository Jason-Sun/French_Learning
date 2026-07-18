/* Browser adapter for Liens' versioned local graph package. */
(()=>{
  class GraphData {
    constructor(root,manifest,lookup){
      this.root=root.replace(/\/$/,'');
      this.manifest=manifest;
      this.objects=lookup.objects||[];
      this.byId=new Map(this.objects.map(object=>[object.id,object]));
      this.loadedShards=new Map();
    }

    static async load(root='data/wordbank/browser'){
      const base=root.replace(/\/$/,'');
      const manifest=await GraphData.fetchJson(base+'/manifest.json');
      const lookup=await GraphData.fetchJson(base+'/'+manifest.lookup.path);
      return new GraphData(base,manifest,lookup);
    }

    static async fetchJson(path){
      const response=await fetch(path);
      if(!response.ok)throw new Error('Could not load local graph data: '+path);
      return response.json();
    }

    object(id){return this.byId.get(id)||null}

    async loadShard(shard){
      if(!this.loadedShards.has(shard)){
        const descriptor=this.manifest.object_shards?.[shard];
        if(!descriptor)throw new Error('Unknown local graph shard: '+shard);
        const loading=GraphData.fetchJson(this.root+'/'+descriptor.path).then(payload=>{
          for(const detail of payload.objects||[]){
            const current=this.byId.get(detail.id);
            if(current)Object.assign(current,detail);
            else {
              this.byId.set(detail.id,detail);
              this.objects.push(detail);
            }
          }
          return payload;
        });
        this.loadedShards.set(shard,loading);
      }
      return this.loadedShards.get(shard);
    }

    async shardFor(id){
      const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(id));
      const value=new DataView(digest).getUint32(0);
      return String(value%64).padStart(2,'0');
    }

    async hydrate(ids){
      const shards=new Set();
      for(const id of ids||[]){
        const object=this.object(id);
        shards.add(object?.detail_shard||await this.shardFor(id));
      }
      await Promise.all([...shards].map(shard=>this.loadShard(shard)));
      return (ids||[]).map(id=>this.object(id)).filter(Boolean);
    }

    conjugationFor(lemmaId){
      return this.manifest.conjugation?.forms_by_lemma_and_tense?.[lemmaId]||{};
    }

    learningGroups(){
      return this.manifest.conjugation?.groups||[];
    }
  }

  window.LiensGraphData=GraphData;
})();
