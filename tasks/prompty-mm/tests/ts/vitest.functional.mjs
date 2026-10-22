export default {
  test: {
    include: ["**/functional/**/*.test.ts"],
    reporters: ["junit"],
    outputFile: {
      junit: "/logs/verifier/functional/ts-results.xml",
    },
  },
};
