import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity()
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true })
  email: string;

  @Column()
  name: string;

  @Column({ nullable: true })
  password: string;

  @Column({ nullable: true })
  push_token: string;

  @Column({ type: 'jsonb', default: { email: true, push: true } })
  preferences: {
    email: boolean;
    push: boolean;
  };
}
