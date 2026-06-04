"use client";

import { Plus, Trash2 } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { getCampaignsApiV1CampaignGet } from '@/client/sdk.gen';
import type { CampaignResponse, CampaignsResponse } from '@/client/types.gen';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Input } from '@/components/ui/input';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { useAuth } from '@/lib/auth';

export default function CampaignsPage() {
    const { user, getAccessToken, redirectToLogin, loading } = useAuth();
    const router = useRouter();

    const [campaignsData, setCampaignsData] = useState<CampaignsResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [campaignToDelete, setCampaignToDelete] = useState<CampaignResponse | null>(null);
    const [confirmName, setConfirmName] = useState('');
    const [isDeleting, setIsDeleting] = useState(false);
    const hasFetched = useRef(false);

    // Redirect if not authenticated
    useEffect(() => {
        if (!loading && !user) {
            redirectToLogin();
        }
    }, [loading, user, redirectToLogin]);

    const fetchCampaigns = useCallback(async () => {
        if (loading || !user) return;
        
        setIsLoading(true);
        try {
            const accessToken = await getAccessToken();
            const response = await getCampaignsApiV1CampaignGet({
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                }
            });

            if (response.data) {
                setCampaignsData(response.data);
            }
        } catch (error) {
            console.error('Failed to fetch campaigns:', error);
            toast.error('Failed to fetch campaigns');
        } finally {
            setIsLoading(false);
        }
    }, [loading, user, getAccessToken]);

    // Fetch campaigns once when user is ready
    useEffect(() => {
        if (loading || !user || hasFetched.current) {
            return;
        }
        hasFetched.current = true;
        fetchCampaigns();
    }, [loading, user, fetchCampaigns]);

    const handleDeleteCampaign = async () => {
        if (!campaignToDelete) return;
        if (confirmName !== campaignToDelete.name) {
            toast.error('Campaign name does not match');
            return;
        }

        setIsDeleting(true);
        try {
            const accessToken = await getAccessToken();
            const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'}/api/v1/campaign/${campaignToDelete.id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                }
            });

            if (response.ok) {
                toast.success('Campaign deleted successfully');
                // Refresh list
                fetchCampaigns();
            } else {
                const errorData = await response.json();
                toast.error(errorData.detail || 'Failed to delete campaign');
            }
        } catch (error) {
            console.error('Failed to delete campaign:', error);
            toast.error('An error occurred while deleting the campaign');
        } finally {
            setIsDeleting(false);
            setCampaignToDelete(null);
            setConfirmName('');
        }
    };

    const handleRowClick = (campaignId: number) => {
        router.push(`/campaigns/${campaignId}`);
    };

    const handleCreateCampaign = () => {
        router.push('/campaigns/new');
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString();
    };

    const getStateBadgeVariant = (state: string) => {
        switch (state) {
            case 'created':
                return 'secondary';
            case 'running':
                return 'default';
            case 'paused':
                return 'outline';
            case 'completed':
                return 'secondary';
            case 'failed':
                return 'destructive';
            default:
                return 'secondary';
        }
    };

    return (
        <div className="container mx-auto p-6 space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold mb-2">Campaigns</h1>
                    <p>Manage your bulk workflow execution campaigns</p>
                </div>
                <Button onClick={handleCreateCampaign} className="bg-yellow-400 hover:bg-yellow-500 text-black">
                    <Plus className="h-4 w-4 mr-2" />
                    Create Campaign
                </Button>
            </div>

            <Card>
                <CardHeader>
                    <CardTitle>All Campaigns</CardTitle>
                    <CardDescription>
                        View and manage your campaigns
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <div className="animate-pulse space-y-3">
                            {[...Array(5)].map((_, i) => (
                                <div key={i} className="h-12 bg-muted rounded"></div>
                            ))}
                        </div>
                    ) : campaignsData?.campaigns && campaignsData.campaigns.length > 0 ? (
                        <div className="overflow-x-auto">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead>Name</TableHead>
                                        <TableHead>Workflow</TableHead>
                                        <TableHead>State</TableHead>
                                        <TableHead>Created</TableHead>
                                        <TableHead className="text-right">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {campaignsData.campaigns.map((campaign) => (
                                        <TableRow
                                            key={campaign.id}
                                            className="cursor-pointer hover:bg-muted/50"
                                            onClick={() => handleRowClick(campaign.id)}
                                        >
                                            <TableCell className="font-medium">{campaign.name}</TableCell>
                                            <TableCell>{campaign.workflow_name}</TableCell>
                                            <TableCell>
                                                <Badge variant={getStateBadgeVariant(campaign.state)}>
                                                    {campaign.state}
                                                </Badge>
                                            </TableCell>
                                            <TableCell>{formatDate(campaign.created_at)}</TableCell>
                                            <TableCell className="text-right whitespace-nowrap">
                                                <div className="flex justify-end items-center gap-3">
                                                    <Button
                                                        variant="destructive"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setCampaignToDelete(campaign);
                                                            setConfirmName('');
                                                        }}
                                                    >
                                                        <Trash2 className="h-4 w-4 mr-2" />
                                                        Delete
                                                    </Button>
                                                    <Button
                                                        variant="outline"
                                                        size="sm"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            handleRowClick(campaign.id);
                                                        }}
                                                    >
                                                        View
                                                    </Button>
                                                </div>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    ) : (
                        <div className="text-center py-8">
                            <p className="mb-4">No campaigns found</p>
                            <Button onClick={handleCreateCampaign} className="bg-yellow-400 hover:bg-yellow-500 text-black">
                                <Plus className="h-4 w-4 mr-2" />
                                Create your first campaign
                            </Button>
                        </div>
                    )}
                </CardContent>
            </Card>

                <AlertDialog open={campaignToDelete !== null} onOpenChange={(open) => {
                    if (!open) {
                        setCampaignToDelete(null);
                        setConfirmName('');
                    }
                }}>
                    <AlertDialogContent>
                        <AlertDialogHeader>
                            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                            <AlertDialogDescription className="space-y-4">
                                <p>
                                    This action cannot be undone. This will permanently delete the campaign
                                    <strong> {campaignToDelete?.name}</strong> and all its associated data.
                                </p>
                                <div className="space-y-2">
                                    <p className="text-sm font-medium text-foreground">
                                        Please type <strong>{campaignToDelete?.name}</strong> to confirm.
                                    </p>
                                    <Input
                                        value={confirmName}
                                        onChange={(e) => setConfirmName(e.target.value)}
                                        placeholder="Type campaign name"
                                        className="border-destructive/50 focus-visible:ring-destructive"
                                    />
                                </div>
                            </AlertDialogDescription>
                        </AlertDialogHeader>
                        <AlertDialogFooter>
                            <AlertDialogCancel disabled={isDeleting}>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                                onClick={(e) => {
                                    e.preventDefault();
                                    handleDeleteCampaign();
                                }}
                                disabled={isDeleting || confirmName !== campaignToDelete?.name}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                            >
                                {isDeleting ? 'Deleting...' : 'Delete Campaign'}
                            </AlertDialogAction>
                        </AlertDialogFooter>
                    </AlertDialogContent>
                </AlertDialog>
        </div>
    );
}
