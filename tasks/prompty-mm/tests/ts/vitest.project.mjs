export default {
  test: {
    include: ["**/project/**/*.test.ts"],
    reporters: ["junit"],
    outputFile: {
      junit: "/logs/verifier/functional/ts_project.xml",
    },
  },
};
