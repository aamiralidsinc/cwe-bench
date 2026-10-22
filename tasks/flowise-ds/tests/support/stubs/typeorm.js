// TypeORM stub: entity decorators are no-ops and the find operators are markers
// the in-memory repository understands.
const noop = () => () => {}
const factories = [
    'Entity',
    'Column',
    'PrimaryGeneratedColumn',
    'PrimaryColumn',
    'CreateDateColumn',
    'UpdateDateColumn',
    'DeleteDateColumn',
    'Index',
    'Unique',
    'ManyToOne',
    'OneToMany',
    'ManyToMany',
    'OneToOne',
    'JoinColumn',
    'JoinTable',
    'Generated',
    'BeforeInsert',
    'BeforeUpdate'
]
const mod = {}
for (const f of factories) mod[f] = () => noop()

mod.Equal = (value) => ({ __op: 'equal', value })
mod.In = (value) => ({ __op: 'in', value })
mod.Not = (value) => ({ __op: 'not', value })
mod.Like = (value) => ({ __op: 'like', value })
mod.IsNull = () => ({ __op: 'isnull' })
mod.MoreThan = (value) => ({ __op: 'morethan', value })
mod.LessThan = (value) => ({ __op: 'lessthan', value })
mod.QueryRunner = class {}
mod.DataSource = class {}
mod.Repository = class {}
mod.EntityManager = class {}

module.exports = mod
