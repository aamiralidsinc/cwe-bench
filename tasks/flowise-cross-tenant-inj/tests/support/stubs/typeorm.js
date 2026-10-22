const noop = () => () => {}
const factories = ['Entity','Column','PrimaryGeneratedColumn','PrimaryColumn','CreateDateColumn','UpdateDateColumn','DeleteDateColumn','Index','Unique','ManyToOne','OneToMany','ManyToMany','OneToOne','JoinColumn','JoinTable','Generated','BeforeInsert','BeforeUpdate']
const mod = {}
for (const f of factories) mod[f] = () => noop()
mod.In = (v) => ({ _type: 'in', value: v })
mod.Not = (v) => ({ _type: 'not', value: v })
mod.Like = (v) => ({ _type: 'like', value: v })
mod.IsNull = () => ({ _type: 'isnull' })
mod.QueryRunner = class {}
mod.DataSource = class {}
mod.Repository = class {}
module.exports = mod
