// Stand-in for the data-access package so the driven API source loads without the full DAL
// runtime. Decorator metadata in the container's tsconfig keeps the import alive, so the
// referenced classes must exist; none of their behaviour is exercised by these suites.
function stubEntity() {}
function stubRepository() {}

module.exports = {
  MessageEntity: stubEntity,
  MessageEntityRepository: stubRepository,
  MessageRepository: stubRepository,
  SubscriberEntity: stubEntity,
  SubscriberRepository: stubRepository,
  EnvironmentEntity: stubEntity,
  EnvironmentRepository: stubRepository,
  JobEntity: stubEntity,
  JobRepository: stubRepository,
  LogRepository: stubRepository,
  NotificationTemplateRepository: stubRepository,
  TopicRepository: stubRepository,
  TopicSubscribersRepository: stubRepository,
  ContextRepository: stubRepository,
  CommunityOrganizationRepository: stubRepository,
  CommunityUserRepository: stubRepository,
  JSONSchemaEntity: stubEntity,
  IntegrationEntity: stubEntity,
  IntegrationRepository: stubRepository,
};
