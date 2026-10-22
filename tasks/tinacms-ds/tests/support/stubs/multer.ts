// Stand-in for multer. The tests hand the handler an already-parsed request
// (req.body / req.file), exactly as multer would leave it; the middleware
// itself only has to complete.

function multer(_options?: any) {
  return {
    single(_field: string) {
      return (req: any, _res: any, next: any) => {
        next(null);
      };
    },
  };
}

// The adapters build a disk storage configuration before calling the
// middleware; it only needs to be accepted.
multer.diskStorage = (options: any) => options;

export default multer;
