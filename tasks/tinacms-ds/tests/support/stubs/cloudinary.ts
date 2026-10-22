// In-memory stand-in for the Cloudinary SDK. Uploads, destroys and search
// expressions are recorded so the tests can assert what reached the service.

export const state = {
  uploads: [] as Array<{ path: string; folder?: string }>,
  destroys: [] as string[],
  searches: [] as string[],
  searchCalls: 0,
  resources: [] as any[],
  folders: [] as any[],
  reset() {
    this.uploads = [];
    this.destroys = [];
    this.searches = [];
    this.searchCalls = 0;
    this.resources = [];
    this.folders = [];
  },
};

const search = {
  _expression: '',
  expression(value: string) {
    state.searches.push(value);
    this._expression = value;
    return this;
  },
  max_results(_n: number) {
    return this;
  },
  next_cursor(_c: string) {
    return this;
  },
  async execute() {
    state.searchCalls += 1;
    return { resources: state.resources, next_cursor: undefined };
  },
};

export const v2 = {
  config(_options: any) {},
  uploader: {
    async upload(path: string, options: any) {
      state.uploads.push({ path, folder: options?.folder });
      return {
        public_id: options?.folder ? `${options.folder}/asset` : 'asset',
        secure_url: 'https://cdn.example/asset',
      };
    },
    destroy(publicId: string, _options: any, callback: any) {
      state.destroys.push(publicId);
      callback(null, { result: 'ok' });
    },
  },
  search,
  api: {
    folders: undefined as any,
    async root_folders() {
      return { folders: state.folders };
    },
    async sub_folders(_directory: string) {
      return { folders: state.folders };
    },
  },
};
