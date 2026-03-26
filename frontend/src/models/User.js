import mongoose from 'mongoose';

const UserSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String },
  role: { type: String, default: 'user', enum: ['user', 'admin'] },
  createdAt: { type: Date, default: Date.now },
resetToken: String,
resetTokenExpiry: Date,

});

export default mongoose.models.User || mongoose.model('User', UserSchema);