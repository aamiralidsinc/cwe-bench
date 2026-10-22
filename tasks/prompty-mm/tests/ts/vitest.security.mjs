export default {
  test: {
    include: ["**/security/**/*.test.ts"],
    reporters: ["junit"],
    outputFile: {
      junit: "/logs/verifier/security/ts-results.xml",
    },
  },
};
